# Arx Web Frontend

## Overview

The Arx Web Frontend is a comprehensive HTML5-based user interface for the Arxos platform, providing interactive building management, version control, asset inventory, and administrative capabilities. Built with modern web technologies, it offers a responsive and intuitive experience for all user roles.

## Tech Stack

- **HTML5** - Semantic markup and structure
- **CSS3** - Modern styling with custom design system
- **JavaScript (ES6+)** - Interactive functionality and API integration
- **Chart.js** - Data visualization and analytics
- **Responsive Design** - Mobile-first approach
- **Progressive Web App** - Offline capabilities and app-like experience

## Features

### Core Functionality
- **Interactive SVG-BIM Viewer** - Real-time building visualization and editing
- **Version Control System** - Floor version history, comparison, and restoration
- **Asset Inventory Management** - Complete building asset tracking and management
- **Role-Based Access Control** - Granular permissions for different user types
- **Real-Time Collaboration** - Multi-user editing with conflict resolution

### Administrative Features
- **User Management** - User registration, role assignment, and access control
- **Security Dashboard** - API key management, security alerts, and monitoring
- **Compliance Reporting** - Data access logs, export analytics, and audit trails
- **System Monitoring** - Performance metrics, error tracking, and health monitoring

### Advanced Features
- **Auto-Snapshot System** - Intelligent automated data protection
- **Data Partitioning** - Large building support with lazy loading
- **CMMS Integration** - Maintenance scheduling and work order management
- **Asset Lifecycle Management** - Replacement schedules and performance analytics
- **Export & Analytics** - Multi-format data export and reporting

## Project Structure

```
arx-web-frontend/
├── index.html                    # Main landing page
├── login.html                    # Authentication interface
├── register.html                 # User registration
├── admin.html                    # Administrative dashboard
├── access_control.html           # Role and permission management
├── version_control.html          # Version control interface
├── floor_version_control.html    # Floor-specific version management
├── svg_view.html                 # Main SVG viewer and editor
├── symbol_generator.html         # Symbol library and generation
├── asset_inventory.html          # Asset management interface
├── connector_management.html     # Data connector management
├── data_vendor_admin.html        # Data vendor administration
├── monitoring.html               # System monitoring dashboard
├── security.html                 # Security management interface
├── compliance.html               # Compliance and audit interface
├── export_analytics.html         # Export analytics and reporting
├── audit_logs.html               # Audit log viewer
├── cmms_settings.html            # CMMS integration settings
├── comments.html                 # Comment and feedback system
├── static/                       # Static assets
│   ├── css/                      # Stylesheets
│   │   ├── main.css              # Main application styles
│   │   ├── access_control.css    # Access control specific styles
│   │   ├── asset_lifecycle.css   # Asset lifecycle styles
│   │   ├── auto_snapshot.css     # Auto-snapshot interface styles
│   │   ├── floor_version.css     # Floor version control styles
│   │   ├── monitoring.css        # Monitoring dashboard styles
│   │   ├── realtime.css          # Real-time features styles
│   │   └── version_control.css   # Version control styles
│   └── js/                       # JavaScript modules
│       ├── access_control_manager.js      # Access control management
│       ├── asset_inventory.js             # Asset inventory operations
│       ├── asset_lifecycle_manager.js     # Asset lifecycle management
│       ├── auto_snapshot_manager.js       # Auto-snapshot system
│       ├── bim_editor_integration.js      # BIM editing integration
│       ├── collaboration_manager.js       # Real-time collaboration
│       ├── compliance_manager.js          # Compliance reporting
│       ├── data_partitioning_manager.js   # Data partitioning
│       ├── export_analytics.js            # Export analytics
│       ├── floor_version_manager.js       # Floor version control
│       ├── integration_points.js          # System integration
│       ├── monitoring_manager.js          # System monitoring
│       ├── realtime_manager.js            # Real-time features
│       ├── route_manager.js               # Route management
│       ├── security_manager.js            # Security management
│       ├── symbol_generator.js            # Symbol generation
│       ├── version_control_manager.js     # Version control
│       └── utils/                         # Utility functions
│           ├── api_client.js              # API client utilities
│           ├── auth_manager.js            # Authentication utilities
│           ├── data_utils.js              # Data processing utilities
│           ├── ui_utils.js                # UI helper functions
│           └── validation.js              # Form validation
├── tests/                        # Test files
│   ├── e2e_tests.js              # End-to-end tests
│   ├── e2e_asset_inventory.js    # Asset inventory E2E tests
│   └── shared/                   # Shared test utilities
│       ├── funding_source_config.js
│       └── funding_source_utils.js
├── FLOOR_VERSION_CONTROL_IMPLEMENTATION.md  # Implementation documentation
├── INTEGRATION_POINTS_IMPLEMENTATION.md     # Integration documentation
└── README.md                     # This file
```

## User Roles & Access Control

### Admin
- **Full System Access** - Complete administrative control
- **User Management** - Create, modify, and delete user accounts
- **Security Management** - API key generation, security monitoring
- **System Configuration** - Platform settings and integrations
- **Audit Access** - Complete audit log and compliance reporting

### Editor
- **Building Management** - Create, edit, and manage building data
- **Version Control** - Create versions, manage branches, resolve conflicts
- **Asset Management** - Full CRUD operations on building assets
- **Collaborative Editing** - Real-time collaboration with other users
- **Export Capabilities** - Generate reports and export data

### Viewer
- **Read-Only Access** - View building data and assets
- **Version History** - Browse version history and comparisons
- **Search & Filter** - Search and filter building data
- **Export (Limited)** - Basic export capabilities

### Maintenance
- **Asset Maintenance** - Update maintenance records and schedules
- **Work Orders** - Create and manage maintenance work orders
- **Lifecycle Tracking** - Monitor asset lifecycle and replacement schedules
- **Limited Editing** - Edit maintenance-related data only

## Key Pages & Features

### Authentication & User Management
- **Login/Register** - Secure authentication with role-based access
- **Admin Dashboard** - Centralized administrative interface
- **Access Control** - Role and permission management

### Building Management
- **SVG Viewer** - Interactive building visualization and editing
- **Version Control** - Complete version management system
- **Floor Version Control** - Floor-specific version operations
- **Symbol Generator** - Building symbol library and generation

### Asset Management
- **Asset Inventory** - Comprehensive asset tracking and management
- **Asset Lifecycle** - Lifecycle tracking and replacement scheduling
- **CMMS Integration** - Maintenance management integration

### System Administration
- **Monitoring Dashboard** - Real-time system monitoring
- **Security Management** - Security alerts and API key management
- **Compliance Reporting** - Audit logs and compliance analytics
- **Export Analytics** - Export tracking and analytics

### Data & Integration
- **Connector Management** - Data connector configuration
- **Data Vendor Admin** - External vendor management
- **Comments System** - User feedback and collaboration

## API Integration

The frontend integrates with multiple backend services:

- **arx-backend** - Main Go backend for core functionality
- **arx_svg_parser** - SVG parsing and BIM processing
- **arx-cmms** - Computerized Maintenance Management System

### Key API Endpoints

```javascript
// Authentication
POST /api/login
POST /api/register
GET /api/me

// Version Control
GET /api/version-control/versions
POST /api/version-control/versions
GET /api/version-control/floors/{floor_id}/history

// Asset Management
GET /api/buildings/{building_id}/assets
POST /api/buildings/{building_id}/assets
PUT /api/buildings/{building_id}/assets/{asset_id}

// Real-time Features
WS /api/realtime/connect
POST /api/realtime/rooms/{room_id}/join
POST /api/realtime/locks/acquire

// Monitoring
GET /api/monitoring/metrics
GET /api/monitoring/health
GET /api/monitoring/api-usage
```

## Development & Testing

### Local Development

1. **Setup**
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd arx-web-frontend
   
   # Serve locally (using any HTTP server)
   python -m http.server 8000
   # or
   npx serve .
   ```

2. **Configuration**
   - Update API endpoints in `static/js/utils/api_client.js`
   - Configure authentication settings
   - Set up environment variables for external services

3. **Testing**
   ```bash
   # Run end-to-end tests
   node tests/e2e_tests.js
   
   # Run specific test suites
   node tests/e2e_asset_inventory.js
   ```

### Testing Strategy

- **Unit Tests** - Individual component testing
- **Integration Tests** - API integration testing
- **E2E Tests** - Complete user workflow testing
- **Cross-Browser Testing** - Browser compatibility testing

## Performance & Optimization

### Loading Optimization
- **Lazy Loading** - Load components on demand
- **Asset Compression** - Minified CSS and JavaScript
- **Caching Strategy** - Browser and CDN caching
- **Progressive Enhancement** - Core functionality works without JavaScript

### Real-Time Features
- **WebSocket Connections** - Real-time collaboration
- **Optimistic Updates** - Immediate UI feedback
- **Conflict Resolution** - Automatic conflict detection and resolution
- **Presence Indicators** - Show active users and their activities

## Security Features

- **JWT Authentication** - Secure token-based authentication
- **Role-Based Access Control** - Granular permission system
- **Input Validation** - Client and server-side validation
- **XSS Protection** - Content Security Policy implementation
- **CSRF Protection** - Cross-Site Request Forgery prevention

## Browser Support

- **Chrome** 90+
- **Firefox** 88+
- **Safari** 14+
- **Edge** 90+

## Deployment

### Production Deployment
- **Static Hosting** - Deploy to CDN or static hosting service
- **HTTPS Required** - Secure connections for all features
- **Environment Configuration** - Production API endpoints and settings
- **Monitoring Integration** - Error tracking and performance monitoring

### Development Deployment
- **Local Development** - HTTP server for local development
- **Staging Environment** - Pre-production testing environment
- **Feature Branches** - Isolated development and testing

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests for new functionality**
5. **Submit a pull request**

## License

© Arxos — Confidential. Internal MVP development only.

---

*For detailed API documentation, see the [Comprehensive API Reference](../arx-docs/COMPREHENSIVE_API_REFERENCE.md)*
