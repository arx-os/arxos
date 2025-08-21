# ARXOS User Guide

## 🎯 **Welcome to ARXOS**

ARXOS is your gateway to intelligent building information - think of it as **"Google Maps for Buildings"**. This guide will help you navigate, explore, and interact with building data at any scale, from campus overviews down to individual circuit traces.

---

## 🚀 **Getting Started**

### **First Time Setup**
1. **Access ARXOS** - Open your browser to the ARXOS application
2. **Upload Building Plans** - Start with a PDF floor plan to create your first building model
3. **Explore the Interface** - Navigate through the 3D building viewer
4. **Validate Data** - Use AR features to verify and improve building information

### **System Requirements**
- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Device**: Desktop, tablet, or mobile device
- **AR Features**: Compatible with 8th Wall AR (iOS/Android)

---

## 🏗️ **Building Navigation**

### **Multi-Scale Exploration**
ARXOS supports 10 levels of zoom, each revealing different detail:

#### **Campus Level (10^4)**
- **View**: Multiple buildings and site layout
- **Actions**: Select buildings, view campus overview
- **Use Case**: Site planning, campus management

#### **Building Level (10^3)**
- **View**: Individual building structure
- **Actions**: Navigate floors, view building systems
- **Use Case**: Building management, facility operations

#### **Floor Level (10^2)**
- **View**: Floor plans with room layouts
- **Actions**: Room navigation, system filtering
- **Use Case**: Space planning, maintenance coordination

#### **Room Level (10^1)**
- **View**: Individual rooms with equipment
- **Actions**: Equipment inspection, system details
- **Use Case**: Room management, equipment tracking

#### **Component Level (10^0)**
- **View**: Individual equipment and fixtures
- **Actions**: Detailed inspection, maintenance records
- **Use Case**: Equipment maintenance, troubleshooting

### **Navigation Controls**
- **Mouse/Touch**: Pan, zoom, rotate
- **Keyboard**: Arrow keys for navigation
- **Touch Gestures**: Pinch to zoom, swipe to rotate
- **AR Mode**: Point device at building for AR overlay

---

## 📊 **System Filtering**

### **Building Systems**
Filter your view to focus on specific building systems:

- **🏗️ Structural** - Walls, beams, columns, foundations
- **⚡ Electrical** - Outlets, switches, panels, wiring
- **🌡️ Mechanical** - HVAC, plumbing, fire protection
- **🚪 Architectural** - Doors, windows, finishes, furniture
- **📡 Telecommunications** - Data, phone, security systems
- **🔬 Specialty** - Medical, laboratory, industrial equipment

### **Filtering Options**
1. **System Toggle** - Click system icons to show/hide
2. **Confidence Filter** - Show only high-confidence data
3. **Detail Level** - Adjust rendering complexity
4. **Validation Status** - Show validated vs. unvalidated objects

---

## 🔍 **Data Exploration**

### **ArxObject Information**
Every building element is an **ArxObject** with rich data:

#### **Basic Information**
- **Type**: What the object represents (outlet, wall, HVAC unit)
- **Name**: Human-readable identifier
- **System**: Which building system it belongs to
- **Location**: Precise 3D coordinates

#### **Technical Details**
- **Specifications**: Voltage, amperage, dimensions, etc.
- **Manufacturer**: Equipment manufacturer and model
- **Installation Date**: When it was installed
- **Maintenance History**: Service records and notes

#### **Confidence Scores**
- **Classification**: How certain we are about the object type
- **Position**: Accuracy of spatial location
- **Properties**: Reliability of technical specifications
- **Overall**: Combined confidence rating

### **Relationship Viewing**
- **Physical Connections**: What feeds what, what contains what
- **Functional Dependencies**: Control systems, monitoring relationships
- **Spatial Relationships**: Adjacent objects, parallel systems

---

## 📱 **AR & 3D Features**

### **Web-Based AR (8th Wall)**
1. **Enable AR Mode** - Click AR button in interface
2. **Point Device** - Aim camera at building or area
3. **View Overlay** - See building data overlaid on real world
4. **Interact** - Tap AR objects for information

### **3D Visualization**
- **Three.js Rendering** - High-performance 3D graphics
- **Lazy Loading** - Smooth performance with large models
- **Level of Detail** - Automatic detail adjustment based on zoom
- **Custom Views** - Save and share specific viewpoints

### **Mobile AR App**
- **Field Validation** - Verify building data on-site
- **Photo Capture** - Document equipment and conditions
- **Measurement Tools** - Take precise measurements
- **Offline Mode** - Work without internet connection

---

## 📤 **Data Ingestion**

### **Uploading Building Plans**
1. **Select File** - Choose PDF, IFC, DWG, or HEIC file
2. **Configure Options** - Set processing preferences
3. **Process** - AI service extracts building information
4. **Review Results** - Check extracted ArxObjects
5. **Validate** - Field-verify important data

### **Supported Formats**
- **PDF**: Floor plans, construction documents
- **IFC**: Building Information Modeling files
- **DWG**: AutoCAD drawing files
- **HEIC**: High-quality photos
- **LiDAR**: Point cloud data

### **Processing Options**
- **Symbol Recognition** - Extract building symbols and equipment
- **Coordinate System** - Automatic or manual coordinate setup
- **Confidence Threshold** - Minimum confidence for extraction
- **System Classification** - Automatic system categorization

---

## ✅ **Data Validation**

### **Field Validation Process**
1. **Identify Objects** - Find ArxObjects in AR/3D view
2. **Collect Data** - Take photos, measurements, notes
3. **Update Information** - Correct errors, add missing data
4. **Boost Confidence** - Improve confidence scores
5. **Verify Relationships** - Confirm connections between objects

### **Validation Tools**
- **AR Overlay** - See building data in real world
- **Photo Capture** - Document current conditions
- **Measurement Tools** - Precise distance and size measurements
- **Note Taking** - Add observations and comments
- **Status Updates** - Mark objects as validated

---

## 🔄 **Real-Time Collaboration**

### **Live Updates**
- **WebSocket Connection** - Real-time data synchronization
- **Multi-User Editing** - Collaborative building updates
- **Change Notifications** - Alerts when data changes
- **Version Control** - Track changes and rollback if needed

### **Collaboration Features**
- **User Roles** - Different permission levels
- **Change Tracking** - Who changed what and when
- **Comment System** - Add notes and discussions
- **Approval Workflow** - Review and approve changes

---

## 📊 **Reporting & Analytics**

### **Building Reports**
- **System Overview** - Complete building system summary
- **Equipment Inventory** - Detailed equipment lists
- **Maintenance Schedule** - Upcoming maintenance tasks
- **Compliance Status** - Code and regulation compliance

### **Export Options**
- **PDF Reports** - Printable building documentation
- **IFC Export** - BIM-compatible file export
- **DWG Export** - AutoCAD-compatible drawings
- **Data Export** - CSV, JSON data exports

---

## 🎨 **Customization**

### **User Preferences**
- **Interface Theme** - Light/dark mode selection
- **Default Views** - Set preferred starting viewpoints
- **Filter Presets** - Save common filter combinations
- **Shortcuts** - Custom keyboard shortcuts

### **Display Options**
- **Color Schemes** - Customize object colors by system
- **Icon Sets** - Choose different symbol representations
- **Detail Levels** - Adjust default rendering detail
- **Performance** - Balance quality vs. speed

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Performance Problems**
- **Reduce Detail Level** - Lower rendering complexity
- **Filter Systems** - Hide unnecessary building systems
- **Close Other Apps** - Free up device resources
- **Check Internet** - Ensure stable connection

#### **AR Issues**
- **Good Lighting** - Ensure adequate lighting for AR
- **Stable Device** - Hold device steady for AR tracking
- **Clear View** - Remove obstacles from camera view
- **Update App** - Ensure latest version

#### **Data Accuracy**
- **Check Confidence** - Look for low-confidence objects
- **Validate Field Data** - Use AR to verify information
- **Review Source** - Check original document quality
- **Contact Support** - Report persistent issues

---

## 📚 **Advanced Features**

### **API Integration**
- **REST API** - Programmatic access to building data
- **Webhooks** - Real-time data change notifications
- **SDK Libraries** - JavaScript, Python, Go client libraries
- **Custom Integrations** - Connect with other systems

### **Automation**
- **Scheduled Reports** - Automatic report generation
- **Data Sync** - Integration with CMMS systems
- **Alert Rules** - Custom notification triggers
- **Workflow Automation** - Automated approval processes

---

## 🆘 **Getting Help**

### **Support Resources**
- **Documentation** - Comprehensive guides and references
- **Video Tutorials** - Step-by-step video instructions
- **Community Forum** - User community discussions
- **Support Team** - Direct technical support

### **Training Options**
- **Online Training** - Self-paced learning modules
- **Live Webinars** - Interactive training sessions
- **On-Site Training** - Customized team training
- **Certification** - ARXOS user certification program

---

## 🎯 **Next Steps**

1. **Upload Your First Plan** - Start with a simple floor plan
2. **Explore the Interface** - Navigate through different zoom levels
3. **Try AR Features** - Test augmented reality on mobile
4. **Validate Data** - Use field validation to improve accuracy
5. **Collaborate** - Invite team members to work together

**Welcome to the future of building intelligence! 🏗️✨**
