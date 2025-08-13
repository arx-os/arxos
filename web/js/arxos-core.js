// Arxos Core JavaScript - Fractal Zoom and ArxObject Management

class ArxosCore {
    constructor() {
        this.currentScale = 1.0;
        this.minScale = 0.001;
        this.maxScale = 100;
        this.viewLevel = 'floor';
        this.objects = new Map();
        this.selectedObject = null;
        this.visibleObjects = new Set();
        this.apiUrl = 'http://localhost:8080/api/v1';
    }

    // Initialize the core system
    async init() {
        console.log('Initializing Arxos Core...');
        await this.loadBuildings();
        this.setupEventListeners();
        this.updateViewLevel();
    }

    // Load available buildings
    async loadBuildings() {
        try {
            const response = await fetch(`${this.apiUrl}/arxobjects?type=building`);
            const buildings = await response.json();
            
            const select = document.getElementById('building-select');
            buildings.forEach(building => {
                const option = document.createElement('option');
                option.value = building.id;
                option.textContent = building.name;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load buildings:', error);
        }
    }

    // Setup event listeners
    setupEventListeners() {
        // Building selection
        document.getElementById('building-select').addEventListener('change', (e) => {
            this.loadBuilding(e.target.value);
        });

        // Zoom controls
        document.getElementById('zoom-in').addEventListener('click', () => {
            this.zoom(1.5);
        });

        document.getElementById('zoom-out').addEventListener('click', () => {
            this.zoom(0.67);
        });

        document.getElementById('zoom-slider').addEventListener('input', (e) => {
            this.setScale(parseFloat(e.target.value));
        });

        // System toggles
        document.querySelectorAll('.system-toggle input').forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                this.toggleSystem(e.target.dataset.system, e.target.checked);
            });
        });
    }

    // Load a building and its objects
    async loadBuilding(buildingId) {
        if (!buildingId) return;

        try {
            // Clear existing objects
            this.clearViewport();

            // Load building hierarchy
            const response = await fetch(`${this.apiUrl}/arxobjects/${buildingId}/children`);
            const children = await response.json();

            // Load all objects recursively
            await this.loadObjectHierarchy(buildingId);

            // Update viewport
            this.updateViewport();
            
            console.log(`Loaded building ${buildingId} with ${this.objects.size} objects`);
        } catch (error) {
            console.error('Failed to load building:', error);
        }
    }

    // Load object hierarchy recursively
    async loadObjectHierarchy(parentId, depth = 0) {
        if (depth > 10) return; // Prevent infinite recursion

        try {
            const response = await fetch(`${this.apiUrl}/arxobjects/${parentId}/children`);
            const children = await response.json();

            for (const child of children) {
                this.objects.set(child.id, child);
                
                // Load grand-children
                if (child.child_ids && child.child_ids.length > 0) {
                    await this.loadObjectHierarchy(child.id, depth + 1);
                }
            }
        } catch (error) {
            console.error(`Failed to load children of ${parentId}:`, error);
        }
    }

    // Clear the viewport
    clearViewport() {
        this.objects.clear();
        this.visibleObjects.clear();
        this.selectedObject = null;

        // Clear SVG layers
        const layers = ['structural', 'mechanical', 'electrical', 'plumbing', 'fire', 'data'];
        layers.forEach(layer => {
            const element = document.getElementById(`${layer}-layer`);
            if (element) element.innerHTML = '';
        });
    }

    // Update viewport with visible objects
    updateViewport() {
        // Get viewport bounds
        const viewport = this.getViewportBounds();
        
        // Query visible objects based on scale and viewport
        this.queryVisibleObjects(viewport);
        
        // Render visible objects
        this.renderObjects();
        
        // Update UI
        this.updateZoomIndicator();
        this.updateViewLevel();
    }

    // Get viewport bounds in world coordinates
    getViewportBounds() {
        const svg = document.getElementById('arxos-svg');
        const rect = svg.getBoundingClientRect();
        
        // Convert screen coordinates to world coordinates
        const scale = this.currentScale;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        return {
            minX: -centerX / scale,
            maxX: centerX / scale,
            minY: -centerY / scale,
            maxY: centerY / scale,
            scale: scale
        };
    }

    // Query objects visible at current scale and viewport
    async queryVisibleObjects(viewport) {
        try {
            const response = await fetch(`${this.apiUrl}/arxobjects/spatial/viewport`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    min_x: viewport.minX,
                    min_y: viewport.minY,
                    max_x: viewport.maxX,
                    max_y: viewport.maxY,
                    scale: viewport.scale,
                    limit: 1000
                })
            });

            const objects = await response.json();
            
            // Update visible objects set
            this.visibleObjects.clear();
            objects.forEach(obj => {
                this.visibleObjects.add(obj.id);
                if (!this.objects.has(obj.id)) {
                    this.objects.set(obj.id, obj);
                }
            });
        } catch (error) {
            console.error('Failed to query visible objects:', error);
        }
    }

    // Render visible objects to SVG
    renderObjects() {
        // Clear layers
        const layers = {
            'structural': document.getElementById('structural-layer'),
            'mechanical': document.getElementById('mechanical-layer'),
            'electrical': document.getElementById('electrical-layer'),
            'plumbing': document.getElementById('plumbing-layer'),
            'fire_protection': document.getElementById('fire-layer'),
            'data': document.getElementById('data-layer')
        };

        Object.values(layers).forEach(layer => {
            if (layer) layer.innerHTML = '';
        });

        // Render each visible object
        this.visibleObjects.forEach(objId => {
            const obj = this.objects.get(objId);
            if (!obj) return;

            const layer = layers[obj.system];
            if (!layer) return;

            // Check if system is enabled
            const systemToggle = document.querySelector(`input[data-system="${obj.system}"]`);
            if (systemToggle && !systemToggle.checked) return;

            // Create SVG element for object
            const element = this.createObjectElement(obj);
            if (element) {
                layer.appendChild(element);
            }
        });
    }

    // Create SVG element for an object
    createObjectElement(obj) {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('data-id', obj.id);
        g.setAttribute('data-type', obj.type);
        g.setAttribute('class', `arxos-object system-${obj.system}`);
        g.setAttribute('transform', `translate(${obj.position_x}, ${obj.position_y})`);

        // Add click handler
        g.addEventListener('click', () => this.selectObject(obj));

        // Render based on scale
        if (this.currentScale > 10) {
            // Campus/Building view - show as icon
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('font-size', '20');
            text.textContent = obj.icon || '📍';
            g.appendChild(text);
        } else if (this.currentScale > 1) {
            // Floor view - show simplified shape
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('width', obj.width || 10);
            rect.setAttribute('height', obj.height || 10);
            rect.setAttribute('fill', this.getSystemColor(obj.system));
            rect.setAttribute('opacity', '0.7');
            g.appendChild(rect);

            // Add label if enabled
            if (document.getElementById('show-labels').checked) {
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('y', -5);
                text.setAttribute('font-size', '8');
                text.textContent = obj.name;
                g.appendChild(text);
            }
        } else {
            // Detail view - show full SVG path if available
            if (obj.svg_path) {
                g.innerHTML = obj.svg_path;
            } else {
                // Default detailed representation
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('r', 5);
                circle.setAttribute('fill', this.getSystemColor(obj.system));
                g.appendChild(circle);
            }

            // Show dimensions if enabled
            if (document.getElementById('show-dimensions').checked && obj.width && obj.height) {
                const dimensionText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                dimensionText.setAttribute('y', obj.height + 10);
                dimensionText.setAttribute('font-size', '6');
                dimensionText.setAttribute('fill', '#666');
                dimensionText.textContent = `${obj.width}x${obj.height}`;
                g.appendChild(dimensionText);
            }
        }

        return g;
    }

    // Get color for system
    getSystemColor(system) {
        const colors = {
            'electrical': '#f59e0b',
            'mechanical': '#6b7280',
            'plumbing': '#3b82f6',
            'fire_protection': '#ef4444',
            'structural': '#8b5cf6',
            'architectural': '#10b981',
            'hvac': '#06b6d4',
            'data': '#ec4899'
        };
        return colors[system] || '#9ca3af';
    }

    // Select an object
    selectObject(obj) {
        this.selectedObject = obj;
        
        // Update selection in viewport
        document.querySelectorAll('.arxos-object').forEach(el => {
            el.classList.remove('selected');
        });
        
        const element = document.querySelector(`[data-id="${obj.id}"]`);
        if (element) {
            element.classList.add('selected');
        }

        // Update details panel
        this.updateDetailsPanel(obj);
        
        // Update status bar
        document.getElementById('selected-object').textContent = obj.name;
    }

    // Update details panel
    updateDetailsPanel(obj) {
        // Update object details
        const detailsDiv = document.getElementById('object-details');
        detailsDiv.innerHTML = `
            <div class="object-info">
                <h4>${obj.name}</h4>
                <p class="object-type">${obj.type}</p>
                <p class="object-id">ID: ${obj.id}</p>
                <p class="object-system">System: ${obj.system}</p>
                ${obj.verified ? '<span class="verified">✓ Verified</span>' : '<span class="unverified">⚠️ Unverified</span>'}
            </div>
        `;

        // Update properties
        const propertiesDiv = document.getElementById('object-properties');
        propertiesDiv.innerHTML = '';
        
        if (obj.properties) {
            Object.entries(obj.properties).forEach(([key, value]) => {
                const item = document.createElement('div');
                item.className = 'property-item';
                item.innerHTML = `
                    <span class="property-label">${key}:</span>
                    <span class="property-value">${value}</span>
                `;
                propertiesDiv.appendChild(item);
            });
        }

        // Update connections
        const connectionsDiv = document.getElementById('object-connections');
        connectionsDiv.innerHTML = '';
        
        if (obj.connections && obj.connections.length > 0) {
            obj.connections.forEach(conn => {
                const item = document.createElement('div');
                item.className = 'connection-item';
                item.innerHTML = `
                    <span class="connection-type">${conn.type}:</span>
                    <span class="connection-target">${conn.to_id}</span>
                `;
                connectionsDiv.appendChild(item);
            });
        }

        // Enable action buttons
        document.getElementById('btn-edit').disabled = false;
        document.getElementById('btn-verify').disabled = obj.verified;
        document.getElementById('btn-report').disabled = false;
    }

    // Zoom in/out
    zoom(factor) {
        this.setScale(this.currentScale * factor);
    }

    // Set scale directly
    setScale(scale) {
        // Clamp scale to valid range
        scale = Math.max(this.minScale, Math.min(this.maxScale, scale));
        
        this.currentScale = scale;
        
        // Update slider
        document.getElementById('zoom-slider').value = scale;
        
        // Update viewport
        this.updateViewport();
    }

    // Update zoom indicator
    updateZoomIndicator() {
        const zoomLevel = document.getElementById('zoom-level');
        
        if (this.currentScale < 0.01) {
            zoomLevel.textContent = `Zoom: ${(this.currentScale * 1000).toFixed(1)}mm`;
        } else if (this.currentScale < 1) {
            zoomLevel.textContent = `Zoom: ${(this.currentScale * 100).toFixed(1)}cm`;
        } else {
            zoomLevel.textContent = `Zoom: ${this.currentScale.toFixed(1)}x`;
        }
    }

    // Update view level based on scale
    updateViewLevel() {
        let level = 'Component';
        
        if (this.currentScale >= 50) {
            level = 'Campus';
        } else if (this.currentScale >= 10) {
            level = 'Building';
        } else if (this.currentScale >= 1) {
            level = 'Floor';
        } else if (this.currentScale >= 0.1) {
            level = 'Room';
        } else if (this.currentScale >= 0.01) {
            level = 'Wall';
        }
        
        this.viewLevel = level;
        document.getElementById('view-level').textContent = `View: ${level}`;
    }

    // Toggle system visibility
    toggleSystem(system, visible) {
        const layer = document.getElementById(`${system}-layer`);
        if (layer) {
            layer.style.display = visible ? 'block' : 'none';
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.arxosCore = new ArxosCore();
    window.arxosCore.init();
});