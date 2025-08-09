# Frontend Architecture - Dual Approach

## 🎯 **Overview**

The Arxos frontend architecture uses a **dual approach** to optimize for different use cases:

1. **HTML/HTMX/CSS/JS** - For landing pages, user interfaces, and general web content
2. **Canvas 2D + Web Workers** - For SVGX engine and CAD functionality

## 🏗️ **Architecture Components**

### **1. Landing Pages & General UI (HTML/HTMX/CSS/JS)**

#### **Technology Stack**
- **HTML**: Semantic markup for accessibility
- **HTMX**: Dynamic interactions without JavaScript frameworks
- **Tailwind CSS**: Utility-first styling
- **Vanilla JavaScript**: Minimal JS for enhanced interactions

#### **Use Cases**
- Landing pages and marketing content
- User authentication and account management
- Project dashboards and file management
- Settings and configuration interfaces
- Documentation and help pages

#### **Example Structure**
```html
<!-- Landing page with HTMX -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arxos Platform</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto px-4">
        <header class="py-6">
            <h1 class="text-3xl font-bold text-gray-900">Arxos Platform</h1>
        </header>

        <main>
            <!-- HTMX-powered content -->
            <div hx-get="/api/projects"
                 hx-trigger="load"
                 hx-target="#project-list">
                <div id="project-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Projects will be loaded here -->
                </div>
            </div>
        </main>
    </div>
</body>
</html>
```

### **2. SVGX Engine & CAD (Canvas 2D + Web Workers)**

#### **Technology Stack**
- **Canvas 2D**: High-performance vector graphics rendering
- **Web Workers**: Background processing for CAD operations
- **JavaScript**: Core CAD functionality and user interactions
- **WebGL** (optional): Advanced 3D rendering when needed

#### **Use Cases**
- SVGX file editing and creation
- CAD drawing and precision tools
- Real-time collaboration on designs
- SVGX engine processing and rendering
- Advanced CAD features (constraints, dimensions)

#### **Example Structure**
```html
<!-- CAD interface with Canvas 2D -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arxos CAD</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white">
    <div class="flex h-screen">
        <!-- Toolbar -->
        <div class="w-64 bg-gray-800 p-4">
            <h2 class="text-xl font-bold mb-4">CAD Tools</h2>
            <div class="space-y-2">
                <button class="w-full p-2 bg-blue-600 rounded" onclick="selectTool('line')">Line</button>
                <button class="w-full p-2 bg-blue-600 rounded" onclick="selectTool('rectangle')">Rectangle</button>
                <button class="w-full p-2 bg-blue-600 rounded" onclick="selectTool('circle')">Circle</button>
            </div>
        </div>

        <!-- Canvas Area -->
        <div class="flex-1 relative">
            <canvas id="cad-canvas" class="w-full h-full bg-white"></canvas>
        </div>

        <!-- Properties Panel -->
        <div class="w-64 bg-gray-800 p-4">
            <h2 class="text-xl font-bold mb-4">Properties</h2>
            <div id="properties-panel">
                <!-- Dynamic properties will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        // Canvas 2D setup
        const canvas = document.getElementById('cad-canvas');
        const ctx = canvas.getContext('2d');

        // Web Worker for background processing
        const cadWorker = new Worker('/static/js/cad-worker.js');

        // CAD functionality
        let currentTool = 'select';

        function selectTool(tool) {
            currentTool = tool;
            // Update UI and tool state
        }

        // Canvas event handlers
        canvas.addEventListener('mousedown', handleMouseDown);
        canvas.addEventListener('mousemove', handleMouseMove);
        canvas.addEventListener('mouseup', handleMouseUp);

        function handleMouseDown(e) {
            // Handle CAD tool interactions
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Process with Web Worker
            cadWorker.postMessage({
                type: 'mouseDown',
                tool: currentTool,
                x: x,
                y: y
            });
        }

        // Web Worker message handling
        cadWorker.onmessage = function(e) {
            const { type, data } = e.data;

            switch(type) {
                case 'render':
                    renderCanvas(data);
                    break;
                case 'updateProperties':
                    updatePropertiesPanel(data);
                    break;
            }
        };

        function renderCanvas(data) {
            // Render SVGX elements to Canvas 2D
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            data.elements.forEach(element => {
                switch(element.type) {
                    case 'line':
                        ctx.beginPath();
                        ctx.moveTo(element.x1, element.y1);
                        ctx.lineTo(element.x2, element.y2);
                        ctx.stroke();
                        break;
                    case 'rectangle':
                        ctx.strokeRect(element.x, element.y, element.width, element.height);
                        break;
                    case 'circle':
                        ctx.beginPath();
                        ctx.arc(element.x, element.y, element.radius, 0, 2 * Math.PI);
                        ctx.stroke();
                        break;
                }
            });
        }
    </script>
</body>
</html>
```

## 🔄 **Integration Strategy**

### **Seamless Navigation**
```html
<!-- Navigation between HTML and Canvas interfaces -->
<nav class="bg-gray-800 text-white p-4">
    <div class="container mx-auto flex justify-between items-center">
        <a href="/" class="text-xl font-bold">Arxos</a>

        <div class="flex space-x-4">
            <a href="/dashboard" class="hover:text-blue-400">Dashboard</a>
            <a href="/projects" class="hover:text-blue-400">Projects</a>
            <a href="/cad" class="hover:text-blue-400">CAD Editor</a>
            <a href="/docs" class="hover:text-blue-400">Documentation</a>
        </div>
    </div>
</nav>
```

### **Shared State Management**
```javascript
// Shared state between HTML and Canvas interfaces
class ArxosState {
    constructor() {
        this.currentUser = null;
        this.currentProject = null;
        this.currentFile = null;
        this.preferences = {};
    }

    // Update state and notify all interfaces
    updateState(newState) {
        Object.assign(this, newState);
        this.notifyInterfaces();
    }

    notifyInterfaces() {
        // Notify HTML interfaces via HTMX
        htmx.trigger(document.body, 'stateChanged', this);

        // Notify Canvas interfaces via custom events
        window.dispatchEvent(new CustomEvent('arxosStateChanged', {
            detail: this
        }));
    }
}

// Global state instance
window.arxosState = new ArxosState();
```

## 📱 **Responsive Design**

### **Mobile-First Approach**
```css
/* Responsive design for both HTML and Canvas interfaces */
@media (max-width: 768px) {
    /* Mobile layout adjustments */
    .cad-toolbar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: rgba(0, 0, 0, 0.9);
    }

    .properties-panel {
        display: none; /* Hide on mobile */
    }

    .canvas-container {
        height: calc(100vh - 60px);
    }
}
```

## 🚀 **Performance Optimization**

### **HTML/HTMX Optimization**
- **Lazy Loading**: Load content on demand
- **Caching**: Browser and server-side caching
- **Minimal JavaScript**: Use HTMX for dynamic content

### **Canvas 2D Optimization**
- **Web Workers**: Background processing for heavy operations
- **RequestAnimationFrame**: Smooth rendering at 60fps
- **Object Pooling**: Reuse objects to reduce garbage collection
- **Culling**: Only render visible elements

```javascript
// Performance optimization example
class CanvasOptimizer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.visibleElements = new Set();
        this.frameId = null;
    }

    startRenderLoop() {
        const render = () => {
            this.renderVisibleElements();
            this.frameId = requestAnimationFrame(render);
        };
        render();
    }

    renderVisibleElements() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Only render visible elements
        this.visibleElements.forEach(element => {
            element.render(this.ctx);
        });
    }

    updateVisibleElements(viewport) {
        this.visibleElements.clear();

        // Cull elements outside viewport
        this.allElements.forEach(element => {
            if (element.isVisible(viewport)) {
                this.visibleElements.add(element);
            }
        });
    }
}
```

## 🔧 **Development Workflow**

### **Component Development**
1. **HTML/HTMX Components**: Landing pages, dashboards, settings
2. **Canvas 2D Components**: CAD tools, SVGX rendering, collaboration
3. **Shared Components**: Navigation, authentication, file management

### **Testing Strategy**
- **HTML Components**: Browser testing with HTMX
- **Canvas Components**: Unit tests for CAD logic, visual regression tests
- **Integration Tests**: End-to-end workflows across both interfaces

## 📊 **Success Metrics**

### **HTML/HTMX Performance**
- **Page Load Time**: < 2 seconds
- **HTMX Response Time**: < 500ms
- **Accessibility Score**: 95%+

### **Canvas 2D Performance**
- **Rendering FPS**: 60fps for complex drawings
- **Memory Usage**: < 100MB for large projects
- **Tool Response Time**: < 16ms for UI interactions

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Status**: Implementation Ready
