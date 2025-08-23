/**
 * Arxos BIM Viewer - Core viewing and interaction logic
 */

class ArxosViewer {
    constructor() {
        this.svg = document.getElementById('bim-viewer');
        this.viewport = document.getElementById('viewport');
        
        // View state
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        
        // Interaction state
        this.isPanning = false;
        this.startX = 0;
        this.startY = 0;
        
        // Data
        this.arxObjects = [];
        this.bounds = null;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Mouse interactions
        this.svg.addEventListener('mousedown', (e) => this.startPan(e));
        this.svg.addEventListener('mousemove', (e) => this.pan(e));
        this.svg.addEventListener('mouseup', () => this.endPan());
        this.svg.addEventListener('mouseleave', () => this.endPan());
        
        // Wheel zoom
        this.svg.addEventListener('wheel', (e) => this.handleWheel(e));
        
        // File upload
        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    }
    
    // View manipulation
    startPan(e) {
        this.isPanning = true;
        this.startX = e.clientX - this.translateX;
        this.startY = e.clientY - this.translateY;
        this.svg.style.cursor = 'grabbing';
    }
    
    pan(e) {
        if (!this.isPanning) return;
        
        e.preventDefault();
        this.translateX = e.clientX - this.startX;
        this.translateY = e.clientY - this.startY;
        this.updateTransform();
    }
    
    endPan() {
        this.isPanning = false;
        this.svg.style.cursor = 'grab';
    }
    
    handleWheel(e) {
        e.preventDefault();
        
        // Get mouse position relative to SVG
        const rect = this.svg.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Calculate zoom
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        const newScale = Math.max(0.1, Math.min(10, this.scale * delta));
        
        // Adjust translation to zoom toward mouse position
        const scaleDiff = newScale - this.scale;
        this.translateX -= x * scaleDiff;
        this.translateY -= y * scaleDiff;
        
        this.scale = newScale;
        this.updateTransform();
        
        // Update scale display
        document.getElementById('scale').textContent = `1:${Math.round(1/this.scale)}`;
    }
    
    updateTransform() {
        this.viewport.setAttribute('transform', 
            `translate(${this.translateX},${this.translateY}) scale(${this.scale})`);
    }
    
    // File handling
    async handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        this.showLoading(true);
        this.updateStatus('Processing PDF...', 'processing');
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            // Using original endpoint (enhanced endpoint coming soon)
            const response = await fetch('http://localhost:8080/upload/pdf', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.arxobjects && data.arxobjects.length > 0) {
                this.arxObjects = data.arxobjects;
                this.renderArxObjects();
                this.updateStatus(`Loaded ${data.arxobjects.length} objects`, 'success');
            } else {
                this.updateStatus('No objects extracted from PDF', 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.updateStatus(`Error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    // Rendering
    renderArxObjects() {
        // Clear all layers
        this.clearAllLayers();
        
        // Reset bounds
        this.bounds = {
            minX: Infinity,
            minY: Infinity,
            maxX: -Infinity,
            maxY: -Infinity
        };
        
        // Group objects by type for proper layering
        const objectsByType = this.groupObjectsByType(this.arxObjects);
        
        // Render in order
        this.renderRooms(objectsByType.rooms || []);
        this.renderWalls(objectsByType.walls || []);
        this.renderColumns(objectsByType.columns || []);
        this.renderDoors(objectsByType.doors || []);
        this.renderWindows(objectsByType.windows || []);
        this.renderTextLabels(objectsByType.texts || []);
        
        // Update stats
        this.updateStats();
        
        // Fit view to content
        this.fitToView();
    }
    
    groupObjectsByType(objects) {
        const groups = {};
        
        objects.forEach(obj => {
            const type = this.getObjectType(obj);
            if (!groups[type]) groups[type] = [];
            groups[type].push(obj);
            
            // Update bounds
            this.updateBounds(obj);
        });
        
        return groups;
    }
    
    getObjectType(obj) {
        // Normalize type detection
        if (obj.type) {
            const type = obj.type.toLowerCase();
            if (type.includes('wall')) return 'walls';
            if (type.includes('room')) return 'rooms';
            if (type.includes('door')) return 'doors';
            if (type.includes('window')) return 'windows';
            if (type.includes('column')) return 'columns';
            if (type.includes('text') || type.includes('label')) return 'texts';
        }
        return 'other';
    }
    
    updateBounds(obj) {
        if (obj.geometry) {
            if (obj.geometry.type === 'LineString') {
                obj.geometry.coordinates.forEach(coord => {
                    this.bounds.minX = Math.min(this.bounds.minX, coord[0]);
                    this.bounds.minY = Math.min(this.bounds.minY, coord[1]);
                    this.bounds.maxX = Math.max(this.bounds.maxX, coord[0]);
                    this.bounds.maxY = Math.max(this.bounds.maxY, coord[1]);
                });
            } else if (obj.geometry.type === 'Polygon') {
                obj.geometry.coordinates[0].forEach(coord => {
                    this.bounds.minX = Math.min(this.bounds.minX, coord[0]);
                    this.bounds.minY = Math.min(this.bounds.minY, coord[1]);
                    this.bounds.maxX = Math.max(this.bounds.maxX, coord[0]);
                    this.bounds.maxY = Math.max(this.bounds.maxY, coord[1]);
                });
            }
        } else if (obj.x !== undefined && obj.y !== undefined) {
            this.bounds.minX = Math.min(this.bounds.minX, obj.x);
            this.bounds.minY = Math.min(this.bounds.minY, obj.y);
            this.bounds.maxX = Math.max(this.bounds.maxX, obj.x + (obj.width || 0));
            this.bounds.maxY = Math.max(this.bounds.maxY, obj.y + (obj.height || 0));
        }
    }
    
    renderWalls(walls) {
        const layer = document.getElementById('wall-layer');
        
        walls.forEach(wall => {
            const confidenceClass = this.getConfidenceClass(wall.confidence);
            
            if (wall.geometry && wall.geometry.type === 'LineString') {
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                const coords = wall.geometry.coordinates;
                
                line.setAttribute('x1', coords[0][0]);
                line.setAttribute('y1', coords[0][1]);
                line.setAttribute('x2', coords[1][0]);
                line.setAttribute('y2', coords[1][1]);
                line.setAttribute('class', `wall ${confidenceClass}`);
                line.setAttribute('stroke-width', wall.thickness || 10);
                
                layer.appendChild(line);
            } else if (wall.x !== undefined) {
                // Legacy format
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', wall.x);
                rect.setAttribute('y', wall.y);
                rect.setAttribute('width', wall.width || 100);
                rect.setAttribute('height', wall.height || 10);
                rect.setAttribute('class', `wall ${confidenceClass}`);
                
                layer.appendChild(rect);
            }
        });
    }
    
    renderRooms(rooms) {
        const layer = document.getElementById('room-layer');
        
        rooms.forEach(room => {
            if (room.geometry && room.geometry.type === 'Polygon') {
                const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                const points = room.geometry.coordinates[0]
                    .map(coord => `${coord[0]},${coord[1]}`)
                    .join(' ');
                
                polygon.setAttribute('points', points);
                polygon.setAttribute('class', 'room');
                polygon.setAttribute('fill-opacity', '0.1');
                polygon.setAttribute('stroke-opacity', '0.5');
                
                // Add room label if available in data
                const roomData = room.data || {};
                const label = roomData.label || room.name || room.label;
                
                if (label) {
                    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    const centroid = roomData.centroid || this.getPolygonCenter(room.geometry.coordinates[0]);
                    text.setAttribute('x', Array.isArray(centroid) ? centroid[0] : centroid.x);
                    text.setAttribute('y', Array.isArray(centroid) ? centroid[1] : centroid.y);
                    text.setAttribute('class', 'text-label');
                    text.setAttribute('text-anchor', 'middle');
                    text.setAttribute('fill', '#4a9eff');
                    text.setAttribute('font-size', '12');
                    text.textContent = label;
                    layer.appendChild(text);
                }
                
                // Show area if available
                if (roomData.area) {
                    const areaText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    const centroid = roomData.centroid || this.getPolygonCenter(room.geometry.coordinates[0]);
                    areaText.setAttribute('x', Array.isArray(centroid) ? centroid[0] : centroid.x);
                    areaText.setAttribute('y', (Array.isArray(centroid) ? centroid[1] : centroid.y) + 15);
                    areaText.setAttribute('class', 'text-label');
                    areaText.setAttribute('text-anchor', 'middle');
                    areaText.setAttribute('fill', '#888');
                    areaText.setAttribute('font-size', '10');
                    areaText.textContent = `${roomData.area.toFixed(1)} m²`;
                    layer.appendChild(areaText);
                }
                
                layer.appendChild(polygon);
            }
        });
    }
    
    renderDoors(doors) {
        const layer = document.getElementById('door-layer');
        
        doors.forEach(door => {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            
            if (door.geometry && door.geometry.type === 'LineString') {
                const coords = door.geometry.coordinates;
                line.setAttribute('x1', coords[0][0]);
                line.setAttribute('y1', coords[0][1]);
                line.setAttribute('x2', coords[1][0]);
                line.setAttribute('y2', coords[1][1]);
            } else {
                line.setAttribute('x1', door.x);
                line.setAttribute('y1', door.y);
                line.setAttribute('x2', door.x + (door.width || 30));
                line.setAttribute('y2', door.y);
            }
            
            line.setAttribute('class', 'door');
            layer.appendChild(line);
        });
    }
    
    renderWindows(windows) {
        const layer = document.getElementById('window-layer');
        
        windows.forEach(window => {
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            
            if (window.x !== undefined) {
                rect.setAttribute('x', window.x);
                rect.setAttribute('y', window.y);
                rect.setAttribute('width', window.width || 40);
                rect.setAttribute('height', window.height || 5);
                rect.setAttribute('class', 'window');
                layer.appendChild(rect);
            }
        });
    }
    
    renderColumns(columns) {
        const layer = document.getElementById('column-layer');
        
        columns.forEach(column => {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            
            if (column.x !== undefined) {
                circle.setAttribute('cx', column.x);
                circle.setAttribute('cy', column.y);
                circle.setAttribute('r', column.radius || 10);
                circle.setAttribute('class', 'column');
                layer.appendChild(circle);
            }
        });
    }
    
    renderTextLabels(texts) {
        const layer = document.getElementById('annotation-layer');
        
        texts.forEach(textObj => {
            if (textObj.geometry && textObj.geometry.type === 'Point') {
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                const coords = textObj.geometry.coordinates;
                
                text.setAttribute('x', coords[0]);
                text.setAttribute('y', coords[1]);
                text.setAttribute('class', 'text-label');
                
                // Check if it's a room label
                const data = textObj.data || {};
                if (data.is_room_label) {
                    text.setAttribute('fill', '#4a9eff');
                    text.setAttribute('font-weight', 'bold');
                    text.setAttribute('font-size', '14');
                } else {
                    text.setAttribute('fill', '#888');
                    text.setAttribute('font-size', '10');
                }
                
                text.setAttribute('text-anchor', 'middle');
                text.textContent = data.text || '';
                
                // Only render if not already associated with a room
                if (!data.associated_room) {
                    layer.appendChild(text);
                }
            }
        });
    }
    
    // Utility functions
    getConfidenceClass(confidence) {
        if (!confidence) return 'confidence-medium';
        if (confidence > 0.8) return 'confidence-high';
        if (confidence > 0.6) return 'confidence-medium';
        return 'confidence-low';
    }
    
    getPolygonCenter(coords) {
        let x = 0, y = 0;
        coords.forEach(coord => {
            x += coord[0];
            y += coord[1];
        });
        return {
            x: x / coords.length,
            y: y / coords.length
        };
    }
    
    clearAllLayers() {
        const layers = [
            'room-layer', 'wall-layer', 'column-layer',
            'door-layer', 'window-layer', 'furniture-layer',
            'annotation-layer', 'dimension-layer'
        ];
        
        layers.forEach(layerId => {
            const layer = document.getElementById(layerId);
            if (layer) layer.innerHTML = '';
        });
    }
    
    fitToView() {
        if (!this.bounds || this.bounds.minX === Infinity) return;
        
        const padding = 50;
        const width = this.bounds.maxX - this.bounds.minX + 2 * padding;
        const height = this.bounds.maxY - this.bounds.minY + 2 * padding;
        
        // Set viewBox
        this.svg.setAttribute('viewBox', 
            `${this.bounds.minX - padding} ${this.bounds.minY - padding} ${width} ${height}`);
        
        // Reset transform
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.updateTransform();
    }
    
    resetView() {
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.updateTransform();
    }
    
    // UI Updates
    updateStatus(message, type = 'normal') {
        const status = document.getElementById('status');
        status.textContent = message;
        status.className = `status-message ${type}`;
    }
    
    updateStats() {
        const stats = {
            objects: this.arxObjects.length,
            walls: this.arxObjects.filter(o => this.getObjectType(o) === 'walls').length,
            confidence: this.calculateAverageConfidence()
        };
        
        document.getElementById('object-count').textContent = stats.objects;
        document.getElementById('wall-count').textContent = stats.walls;
        document.getElementById('confidence').textContent = 
            stats.confidence > 0 ? `${Math.round(stats.confidence * 100)}%` : '-';
    }
    
    calculateAverageConfidence() {
        if (this.arxObjects.length === 0) return 0;
        
        const sum = this.arxObjects.reduce((acc, obj) => 
            acc + (obj.confidence || 0.5), 0);
        
        return sum / this.arxObjects.length;
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loading');
        overlay.classList.toggle('active', show);
    }
}

// Global functions for controls
let viewer;

function selectFile() {
    document.getElementById('file-input').click();
}

function zoomIn() {
    viewer.scale *= 1.2;
    viewer.updateTransform();
}

function zoomOut() {
    viewer.scale *= 0.8;
    viewer.updateTransform();
}

function fitToView() {
    viewer.fitToView();
}

function resetView() {
    viewer.resetView();
}

// Initialize viewer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    viewer = new ArxosViewer();
});